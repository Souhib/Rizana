email_body = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activate Your Account</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
            color: #333;
        }
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .button {
            display: inline-block;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #007BFF;
            color: #ffffff;
            text-decoration: none;
            border-radius: 4px;
            font-size: 16px;
        }
        .button:hover {
            background-color: #0056b3;
        }
        .footer {
            font-size: 12px;
            color: #666;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <h1>Activate Your Account</h1>
        <p>Hi [User's Name],</p>
        <p>Welcome to <strong>Rizana</strong>! Click the button below to activate your account and get started:</p>
        <a href="http://localhost:8000/users/activate?user_id=[User ID]&activation_key=[User Activation Key]" class="button">Activate My Account</a>
        <p>If you didn't sign up for a Rizana account, please ignore this email.</p>
        <div class="footer">
            <p>Thanks for joining us!<br>The Rizana Team</p>
        </div>
    </div>
</body>
</html>
"""

email_success = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Activated</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
            color: #333;
        }
        .success-container {
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .success-container h1 {
            color: #28a745;
        }
        .button {
            display: inline-block;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #007BFF;
            color: #ffffff;
            text-decoration: none;
            border-radius: 4px;
            font-size: 16px;
        }
        .button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="success-container">
        <h1>Account Activated Successfully!</h1>
        <p>Thank you for activating your account. You can now log in and start using our services.</p>
        <a href="http://localhost:8000/login" class="button">Go to Login</a>
    </div>
</body>
</html>
"""
