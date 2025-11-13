# app/ai_service.py
"""
Servicio de IA para análisis de estudiantes usando Google Gemini
"""
import os
import json
from typing import List, Dict
import google.generativeai as genai

def get_gemini_model():
    """Configurar y obtener modelo de Gemini"""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY no está configurada en el .env")
    
    genai.configure(api_key=api_key)
    
    
    model = genai.GenerativeModel('gemini-pro')
    return model

def analyze_student_for_career(student_name: str, notes: List[Dict]) -> Dict:
    """
    Analizar las notas de un estudiante y generar sugerencias de carrera.
    
    Args:
        student_name: Nombre completo del estudiante
        notes: Lista de diccionarios con las notas de los maestros
               Cada nota debe tener: {note: str, category: str, date: str}
    
    Returns:
        Dict con el análisis y sugerencias de carreras
    """
    
    # Si no hay notas, retornar mensaje indicándolo
    if not notes or len(notes) == 0:
        return {
            "status": "insufficient_data",
            "message": "No hay suficientes notas para realizar un análisis significativo",
            "career_suggestions": [],
            "analysis": "Se requieren al menos algunas observaciones de maestros para poder generar sugerencias de carrera."
        }
    
    # Construir el prompt para Gemini
    notes_text = "\n".join([
        f"- [{note['category']}] {note['note']} (Fecha: {note['date']})"
        for note in notes
    ])
    
    prompt = f"""Eres un orientador vocacional experto en México. Analiza las siguientes observaciones de maestros sobre el estudiante {student_name}.

OBSERVACIONES DE MAESTROS:
{notes_text}

Basándote en estas observaciones, proporciona tu análisis en formato JSON con esta estructura EXACTA (sin markdown, sin ```json, solo el JSON puro):

{{
    "student_summary": "Resumen breve del perfil del estudiante en 2-3 oraciones",
    "strengths": ["fortaleza 1", "fortaleza 2", "fortaleza 3"],
    "interests": ["interés identificado 1", "interés identificado 2"],
    "career_suggestions": [
        {{
            "career": "Nombre de la carrera universitaria",
            "match_percentage": 85,
            "reasoning": "Explicación específica de por qué esta carrera es adecuada basada en las observaciones",
            "related_skills": ["habilidad relevante 1", "habilidad relevante 2"]
        }},
        {{
            "career": "Segunda carrera universitaria",
            "match_percentage": 80,
            "reasoning": "Razón específica para esta carrera",
            "related_skills": ["habilidad 1", "habilidad 2"]
        }},
        {{
            "career": "Tercera carrera universitaria",
            "match_percentage": 75,
            "reasoning": "Razón específica para esta carrera",
            "related_skills": ["habilidad 1", "habilidad 2"]
        }}
    ],
    "recommendations": "Recomendaciones específicas para el estudiante y sus padres"
}}

IMPORTANTE: 
- Sugiere carreras universitarias relevantes para México (Ingeniería en sus variantes, Medicina, Derecho, Administración, Psicología, Arquitectura, etc.)
- Basa tus sugerencias DIRECTAMENTE en las observaciones proporcionadas
- Sé MUY específico en tus razonamientos, menciona qué observación justifica cada sugerencia
- Los porcentajes deben reflejar qué tan bien coinciden las observaciones con cada carrera
- Responde ÚNICAMENTE con el JSON válido, sin texto adicional antes o después, sin bloques de código markdown"""

    try:
        # Llamar a Gemini
        model = get_gemini_model()
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Limpiar la respuesta (remover markdown si existe)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Intentar parsear JSON
        try:
            # Buscar el JSON en la respuesta
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                analysis = json.loads(json_text)
                analysis["status"] = "success"
                analysis["raw_response"] = response_text
                return analysis
            else:
                # Si no hay JSON, crear estructura básica
                return {
                    "status": "partial_success",
                    "student_summary": f"Análisis generado para {student_name}",
                    "strengths": ["Requiere análisis manual"],
                    "interests": ["Basado en observaciones de maestros"],
                    "career_suggestions": [
                        {
                            "career": "Análisis en proceso",
                            "match_percentage": 70,
                            "reasoning": "Se requiere revisión del análisis completo",
                            "related_skills": ["En evaluación"]
                        }
                    ],
                    "recommendations": "Revisar análisis completo en campo raw_response",
                    "raw_response": response_text
                }
        
        except json.JSONDecodeError as e:
            return {
                "status": "parse_error",
                "message": f"No se pudo parsear la respuesta como JSON: {str(e)}",
                "raw_analysis": response_text,
                "career_suggestions": []
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al llamar a Gemini API: {str(e)}",
            "career_suggestions": []
        }

def generate_student_report(student_data: Dict) -> str:
    """
    Generar un reporte completo en texto del estudiante.
    
    Args:
        student_data: Diccionario con toda la información del estudiante
    
    Returns:
        String con el reporte formateado
    """
    
    prompt = f"""Genera un reporte profesional de orientación vocacional para el siguiente estudiante mexicano:

INFORMACIÓN DEL ESTUDIANTE:
- Nombre: {student_data['name']}
- Nivel educativo: {student_data.get('grade_level', 'No especificado')}
- Tasa de asistencia: {student_data.get('attendance_rate', 0)}%
- Total de asistencias: {student_data.get('total_attendances', 0)} días

OBSERVACIONES DE MAESTROS:
{student_data.get('notes_summary', 'No hay observaciones registradas')}

ANÁLISIS DE CARRERA PREVIO:
{student_data.get('career_analysis', 'No disponible')}

Por favor genera un reporte profesional y detallado en español que incluya las siguientes secciones:

1. RESUMEN EJECUTIVO
   - Descripción general del estudiante
   - Aspectos más destacados

2. ANÁLISIS DE DESEMPEÑO Y COMPROMISO
   - Evaluación de la asistencia ({student_data.get('attendance_rate', 0)}%)
   - Interpretación del compromiso académico
   - Patrones observados

3. FORTALEZAS Y ÁREAS DE INTERÉS IDENTIFICADAS
   - Lista detallada de fortalezas basadas en observaciones
   - Áreas de interés evidenciadas
   - Habilidades destacadas

4. SUGERENCIAS DE CARRERAS UNIVERSITARIAS
   - 3-5 carreras universitarias específicas recomendadas
   - Justificación detallada para cada carrera
   - Compatibilidad con el perfil del estudiante

5. RECOMENDACIONES PARA PADRES Y TUTORES
   - Cómo apoyar el desarrollo vocacional
   - Actividades extracurriculares sugeridas
   - Recursos educativos recomendados

6. PLAN DE ACCIÓN Y PRÓXIMOS PASOS
   - Acciones concretas a corto plazo (1-3 meses)
   - Acciones a mediano plazo (6-12 meses)
   - Hitos importantes a considerar

El reporte debe ser:
- Profesional pero accesible para padres y estudiantes
- Constructivo y motivador
- Específico y basado en evidencia de las observaciones
- Orientado a la acción

Formato: Usa encabezados claros, párrafos bien estructurados y listas cuando sea apropiado."""

    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"Error al generar el reporte: {str(e)}\n\nPor favor verifica que la API key de Gemini esté configurada correctamente en el archivo .env"

def batch_analyze_students(students_data: List[Dict]) -> Dict:
    """
    Analizar múltiples estudiantes a la vez y generar un resumen institucional.
    
    Args:
        students_data: Lista de diccionarios con información de estudiantes
    
    Returns:
        Diccionario con análisis agregado
    """
    
    if not students_data:
        return {
            "status": "error",
            "message": "No se proporcionaron datos de estudiantes"
        }
    
    students_summary = "\n\n".join([
        f"ESTUDIANTE {i+1}: {s['name']}\n" +
        f"Nivel: {s.get('grade_level', 'N/A')}\n" +
        f"Observaciones destacadas:\n" + "\n".join([f"  - {n}" for n in s.get('key_notes', [])[:3]])  # Máximo 3 notas por estudiante
        for i, s in enumerate(students_data)
    ])
    
    prompt = f"""Analiza el siguiente grupo de {len(students_data)} estudiantes mexicanos desde una perspectiva institucional.

DATOS DE ESTUDIANTES:
{students_summary}

Como orientador educativo institucional, proporciona un análisis en formato JSON (sin markdown, solo JSON puro):

{{
    "total_students": {len(students_data)},
    "common_patterns": [
        "Patrón común identificado 1 en el grupo",
        "Patrón común identificado 2 en el grupo",
        "Patrón común identificado 3 en el grupo"
    ],
    "interest_distribution": {{
        "academico": 0,
        "deportivo": 0,
        "artistico": 0,
        "social": 0
    }},
    "recommendations_for_school": [
        "Recomendación institucional específica 1",
        "Recomendación institucional específica 2",
        "Recomendación institucional específica 3",
        "Recomendación institucional específica 4"
    ],
    "summary": "Resumen ejecutivo del análisis grupal en 3-4 oraciones que destaque los hallazgos más importantes"
}}

IMPORTANTE:
- En interest_distribution, coloca el NÚMERO de estudiantes que muestran cada tipo de interés (la suma puede ser mayor que el total si hay estudiantes con múltiples intereses)
- Las recomendaciones deben ser ACCIONABLES y específicas para la institución
- Basa tu análisis en las observaciones proporcionadas
- Responde SOLO con el JSON válido, sin texto adicional"""

    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Limpiar markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_text = response_text[start_idx:end_idx]
            
            analysis = json.loads(json_text)
            analysis["status"] = "success"
            
            return analysis
        except json.JSONDecodeError:
            return {
                "status": "partial_success",
                "message": "Análisis generado pero no en formato JSON estructurado",
                "raw_analysis": response_text
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en análisis grupal: {str(e)}"
        }
