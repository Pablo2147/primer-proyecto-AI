from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
    plantilla_analizar = PromptTemplate.from_template(
        "Analiza la siguiente reseña de un cliente. Indica el sentimiento "
        "(positivo, neutral o negativo) y de 2 a 3 puntos clave, uno por "
        "línea:\n\n{resena}"
    )
    paso_analizar = plantilla_analizar | modelo | StrOutputParser()

    plantilla_decidir = PromptTemplate.from_template(
        "Con base en este análisis de una reseña, indica la acción "
        "recomendada para la marca (agradecer, disculparse y ofrecer "
        "solución, o aclarar un malentendido) y repite los puntos clave "
        "que hay que atender:\n\n{analisis}"
    )
    paso_decidir = plantilla_decidir | modelo | StrOutputParser()

    plantilla_redactar = PromptTemplate.from_template(
        "Redacta la respuesta pública de la marca a la reseña, en español, "
        "cordial y de máximo 4 líneas, siguiendo esta acción y estos "
        "puntos:\n\n{accion}"
    )
    paso_redactar = plantilla_redactar | modelo | StrOutputParser()

    return (
        paso_analizar
        | (lambda analisis: {"analisis": analisis})
        | paso_decidir
        | (lambda accion: {"accion": accion})
        | paso_redactar
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    cadena = construir_cadena(modelo)

    texto_entrada = (
        "El producto llegó una semana tarde y la caja venía rota, "
        "pero el soporte fue amable al responderme."
    )

    resultado = cadena.invoke({"resena": texto_entrada})
    print(resultado)
