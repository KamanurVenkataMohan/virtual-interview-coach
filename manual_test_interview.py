from modules.interview import Interview


def main():
    interview = Interview(role="Python Developer")

    for i in range(3):
        q = interview.ask_question()

        print("\n--------------------------------")
        print(f"Question {i+1}")
        print("--------------------------------")
        print(q["question"])


if __name__ == "__main__":
    main()