# AI Interview Simulator

## Overview
The AI Interview Simulator is a web application built using Flask that conducts mock interviews automatically. It features a variety of technical and HR questions, performs voice analysis to assess the candidate's confidence, and provides performance scoring based on responses.

## Features
- **Mock Interviews**: Conducts simulated interviews with a mix of technical and HR questions.
- **Voice Analysis**: Analyzes the candidate's voice to evaluate confidence levels during responses.
- **Performance Scoring**: Scores the candidate's performance based on their answers and voice analysis.

## Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ai-interview-simulator.git
   cd ai-interview-simulator
   ```

2. **Create a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```bash
   set FLASK_APP=app.py
   flask run
   ```

   If you are using PowerShell, use:
   ```powershell
   $env:FLASK_APP = 'app.py'
   .venv\Scripts\flask.exe run
   ```

   Or use a direct Python command to avoid shell-specific syntax:
   ```powershell
   $env:FLASK_APP = 'app.py'
   .venv\Scripts\python.exe -m flask run
   ```

## Usage Guidelines
- Visit the app in your browser at `http://127.0.0.1:5000`.
- Choose either HR or Technical interview mode, answer the questions, and submit.
- The site will score your performance and give a confidence summary.
- Interview results are stored in `data/interview_results.json` for later review.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.