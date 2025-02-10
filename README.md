# website-project

## How to run the template?

1. **Create a virtual environment**:
   - In your terminal or command line, navigate to your project directory.
   - Run the following command to create a virtual environment:
     ```bash
     python -m venv venv
     ```
   
2. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install the required dependencies**:
   - After activating the virtual environment, install the required packages by running:
     ```bash
     pip install -r requirements.txt
     ```

4. **Set up environment variables**:
   - Replace the `os.getenv()` calls in your project with actual values in the `.env` file.
   - Make sure to create a `.env` file in the root of your project, and add the following variables (or any others that your project needs):
     ```env
     SECRET_KEY=your_secret_key
     api_key=your_stripe_api_key
     MAIL_USERNAME=your_email
     MAIL_PASSWORD=your_email_password
     ```

5. **Run the project**:
   - To start the Flask application, run the following command:
     ```bash
     flask run
     ```
   - This will start the server on `http://127.0.0.1:5000/`, or any other port that is specified.

## Technologies used in this project

- Flask
- Python
- Bootstrap
- CSS3
- HTML5
