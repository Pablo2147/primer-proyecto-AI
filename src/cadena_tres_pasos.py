from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
    plantilla_traducir = PromptTemplate.from_template(
        "Traduce el siguiente texto al español, de forma natural:\n\n{texto}"
    )
    paso_traducir = plantilla_traducir | modelo | StrOutputParser()

    plantilla_resumir = PromptTemplate.from_template(
        "Lee el siguiente texto y devuelve sus 2 o 3 ideas "
        "principales, una por línea, sin desarrollarlas:"
        "\n\n{traduccion}"
    )
    paso_resumir = plantilla_resumir | modelo | StrOutputParser()

    plantilla_formato = PromptTemplate.from_template(
        "Convierte estas ideas en una lista de viñetas "
        "markdown, sin introducción:\n\n{ideas}"
    )
    paso_formato = plantilla_formato | modelo | StrOutputParser()

    return (
        paso_traducir
        | (lambda traduccion: {"traduccion": traduccion})
        | paso_resumir
        | (lambda ideas: {"ideas": ideas})
        | paso_formato
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    cadena = construir_cadena(modelo)

    texto_entrada = (
        "Large language models learn patterns from massive "
        "amounts of text during training, but they do not "
        "store exact copies of that text. Instead, they "
        "learn statistical relationships between words and "
        "concepts, which lets them generate new text "
        "without literally reproducing their training data."
    )

    resultado = cadena.invoke({"texto": texto_entrada})
    print(resultado)
