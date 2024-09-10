document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const chatForm = document.getElementById('chatForm');
    const loginMessage = document.getElementById('login-message');
    const signupMessage = document.getElementById('signup-message');
    const responseText = document.getElementById('response-text');

    document.getElementById('show-signup').addEventListener('click', () => {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('signup-form').style.display = 'block';
    });

    document.getElementById('show-login').addEventListener('click', () => {
        document.getElementById('signup-form').style.display = 'none';
        document.getElementById('login-form').style.display = 'block';
    });

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(loginForm);
        const data = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        loginMessage.textContent = result.message;

        if (result.message === 'Login successful!') {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('chat').style.display = 'block';
        }
    });

    signupForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(signupForm);
        const data = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        const response = await fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        signupMessage.textContent = result.message;
    });

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(chatForm);
        const question = formData.get('question');

        const response = await fetch('/ask?username=' + encodeURIComponent(document.getElementById('login-username').value), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        const result = await response.json();
        responseText.textContent = result.response;
    });
});
