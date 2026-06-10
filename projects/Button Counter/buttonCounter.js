// console.log(`Hello`);
// console.log(`I like pizza!`);
// window.alert(`This is an alert!`);
// window.alert(`I like pizza!`);

// document.getElementById("myH1").textContent = `Hello`;
// document.getElementById('myP').textContent = `I like pizza!`;

// //This is a comment
// /*  This
//     is 
//     a 
//     comment
// */

// let age = 25;
// let price = 11.99;
// let gpa = 2.1;

// console.log(typeof );
// console.log(`You are ${age} years old.`);
// console.log(`The price is $${price}`);
// console.log(`Your gpa is: ${gpa}`);


// let name = 'erkut';
// let favoriteFood = 'burger';
// let email = 'aerkut@gmail.com';

// console.log(typeof name);
// console.log(`Your name is ${name}`);
// console.log(`Your favorite food is ${favoriteFood}`);
// console.log(`Your e mail: ${email}`);

// let fullName = 'AYDIN ERKUT';
// let age = 25;
// let student = false; 
// document.getElementById("p1").textContent = `Your name is ${fullName}`;
// document.getElementById("p2").textContent = `Your age is ${age} years old`;
// document.getElementById("p3").textContent = `Enrolled: ${student}`;

// let student = 30;
// student = student ** 2;

// student += 1;
// student -= 2;
// student *= 2;
// student /= 2;
// student **= 2;
// student ++;
// student -- 2;

// document.getElementById("p3").textContent = student;

/*
operator precedence
1. parenthesis ()
2. exponents
3. multiplication & division & modulo
4. addition & subtraction 
*/

// let username;

// document.getElementById("mySubmit").onclick = function(){
//     username = document.getElementById("myText").value;
//     console.log(username);

// }

// let age = window.prompt("How old are you?");
// age = Number(age);
// age +=1;
// console.log(age, typeof age);


const decreaseBtn = document.getElementById("decreaseBtn");
const resetBtn = document.getElementById("resetBtn");
const increaseBtn = document.getElementById("increaseBtn");
const countLabel = document.getElementById("countLabel");
let count = 0;

increaseBtn.onclick = function(){
    count++;
    countLabel.textContent = count;
}
decreaseBtn.onclick = function(){
    count--;
    countLabel.textContent = count;
}
resetBtn.onclick = function(){
    count = 0;
    countLabel.textContent = count;
}
