from modules.ai_service import generate_question

ROLE_TOPICS = {

    "Python Developer": [
        "Python Basics",
        "OOP",
        "Strings",
        "Lists",
        "Exception Handling",
        "File Handling",
        "SQL",
        "DBMS",
        "Data Structures",
        "Algorithms"
    ],

    "Java Developer": [
        "Core Java",
        "OOP",
        "Collections Framework",
        "Exception Handling",
        "Multithreading",
        "JDBC",
        "Spring Boot",
        "SQL",
        "Data Structures",
        "Algorithms"
    ],

    "Full Stack Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "React",
        "Node.js",
        "Express.js",
        "MongoDB",
        "REST APIs",
        "Authentication",
        "System Design"
    ],

    "Frontend Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "React",
        "Bootstrap",
        "Tailwind CSS",
        "DOM",
        "Responsive Design",
        "REST APIs",
        "Performance Optimization"
    ],

    "Backend Developer": [
        "Python",
        "Flask",
        "Django",
        "REST APIs",
        "Authentication",
        "SQL",
        "MongoDB",
        "Caching",
        "System Design",
        "Microservices"
    ],

    "AI/ML Engineer": [
        "Python",
        "NumPy",
        "Pandas",
        "Machine Learning",
        "Deep Learning",
        "TensorFlow",
        "Scikit-Learn",
        "NLP",
        "Computer Vision",
        "Model Evaluation"
    ],

    "Data Scientist": [
        "Python",
        "Statistics",
        "Probability",
        "Pandas",
        "NumPy",
        "SQL",
        "Machine Learning",
        "Feature Engineering",
        "Data Visualization",
        "Model Evaluation"
    ],

    "Data Analyst": [
        "SQL",
        "Excel",
        "Python",
        "Pandas",
        "Data Cleaning",
        "Statistics",
        "Power BI",
        "Tableau",
        "Data Visualization",
        "Business Analytics"
    ],

    "DevOps Engineer": [
        "Linux",
        "Git",
        "Docker",
        "Kubernetes",
        "CI/CD",
        "AWS",
        "Terraform",
        "Monitoring",
        "Networking",
        "Security"
    ],

    "Cloud Engineer": [
        "AWS",
        "Azure",
        "Google Cloud",
        "Virtual Machines",
        "Networking",
        "Docker",
        "Kubernetes",
        "Load Balancing",
        "Cloud Security",
        "Monitoring"
    ],

    "Cyber Security Analyst": [
        "Networking",
        "Cryptography",
        "OWASP",
        "Web Security",
        "Authentication",
        "Firewalls",
        "Penetration Testing",
        "Incident Response",
        "Malware Analysis",
        "Security Tools"
    ]
}


class Interview:

    def __init__(self, questions=None, role="Python Developer"):
        self.role = role
        self.difficulty = "Easy"
        self.previous_questions = []
        self.responses = []
        self.questions = questions or [{
            "question": "Interview ready",
            "difficulty": self.difficulty,
            "topic": ROLE_TOPICS.get(role, ROLE_TOPICS["Python Developer"])[0]
        }]

        # Select topics based on the selected role
        self.topics = ROLE_TOPICS.get(role, ROLE_TOPICS["Python Developer"])

        self.current_topic = 0

    def ask_question(self):
        if self.current_topic >= len(self.topics):
            return None

        topic = self.topics[self.current_topic]

        question = generate_question(
            role=self.role,
            difficulty=self.difficulty,
            topic=topic,
            previous_questions=self.previous_questions
        )

        self.previous_questions.append(question)

        question_data = {
            "question": question,
            "difficulty": self.difficulty,
            "topic": topic
        }

        self.questions.append(question_data)
        self.current_topic += 1

        return question_data

    def collect_response(self, question, response):
        self.responses.append({
            "question": question,
            "response": response
        })
        return response

    def conduct_interview(self):
        if not self.responses and self.questions:
            for question in self.questions:
                self.responses.append({
                    "question": question.get("question", ""),
                    "response": ""
                })
        return self.responses

    def reset_interview(self):
        self.previous_questions.clear()
        self.responses.clear()
        self.questions.clear()
        self.current_topic = 0