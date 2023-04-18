// var fs = require('fs');

var form = document.getElementById("message_input_form");
form.onsubmit = function(e) {
    e.preventDefault();

    let username = document.getElementById("username");
    let password = document.getElementById("password");
    alert(username.value);

    const cars = [
        { "make": "Porsche", "model": "911S" },
        { "make": "Mercedes-Benz", "model": "220SE" },
        { "make": "Jaguar", "model": "Mark VII" },
    ];

    const hashed_password = CryptoJS.SHA256(password)
    const user_info = { "username": username, "password": password };
    

    if (username.value.length && password.value.length) {
        getData();
        postData(cars);
    }
};

function getData() {
    fetch("/get")
        .then(function(response) {
            return response.json();
        }).then(function(text) {
            console.log("GET response:");
            console.log(text.greeting);
        });
}

function postData(data) {
    fetch("/post", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
        },
        body: JSON.stringify(data),
    }).then((res) => {
        if (res.ok) {
            return res.json();
        } else {
            alert("something is wrong");
        }
    }).then((jsonResponse) => {
        // Log the response data in the console
        console.log(jsonResponse);
    }).catch((err) => console.error(err));
}
// console.log("js works");
