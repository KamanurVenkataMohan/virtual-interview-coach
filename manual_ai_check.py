from modules.ai_service import ask_ai


def main():
    question = ask_ai(
        "Generate one Python interview question. Return only the question."
    )
    print(question)


if __name__ == "__main__":
    main()