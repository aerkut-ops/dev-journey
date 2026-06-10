const basvuranlar = Array.from(
    { length: 100 },
    (_, i) => `user${i + 1}`
);

function lottery (basvuranlar){
    const kazananlar = [];
    const basvuranlarKopya = [...basvuranlar];

    for (let i = 0; i < 5; i++){
    kazananlar.push(basvuranlar[i]);
    }
    for (let i = 9; i <50; i+=10){
    kazananlar.push(basvuranlar[i]);
    }
    for (let i = 49; i >= 9; i -= 10){
        basvuranlarKopya.splice(i, 1);
    }
    basvuranlarKopya.splice(0, 5);
    const rastgaleKazanan = basvuranlarKopya[Math.floor(Math.random()*basvuranlarKopya.length)];
    kazananlar.push(rastgaleKazanan);
    return kazananlar;
}

console.log(lottery(basvuranlar));