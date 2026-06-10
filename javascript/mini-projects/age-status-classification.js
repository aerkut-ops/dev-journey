let metin = "";
const birthYear = 1978;
const name = "Oğuz";
let status = "";
let age = 2023 - birthYear;

if (age < 12) {
  status = "Çocuk";
} else if (age >= 12 && age < 18) {
  status = "Genç";
} else {
  status = "Yaşlı";
}

metin = name + "'un statüsü: " + status;
console.log(metin);