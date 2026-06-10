function tasKagitMakas(secim) {
    const secimler = [`taş`, `kağıt`, `makas`];
    let pcSecim = secimler[Math.floor(Math.random() * 3)];

    if (!secimler.includes(secim)) {
        return "Yanlış giriş yaptın.";
    }

    if (secim === pcSecim) {
        return `Beraberlik! Senin: ${secim}, Bilgisayar: ${pcSecim}`;
    } else if (
        (secim === 'taş' && pcSecim === 'makas') ||
        (secim === 'kağıt' && pcSecim === 'taş') ||
        (secim === 'makas' && pcSecim === 'kağıt')
    ) {
        return `Kazandın! Senin: ${secim}, Bilgisayar: ${pcSecim}`;
    } else {
        return `Bilgisayar kazandı! Senin: ${secim}, Bilgisayar: ${pcSecim}`;
    }
}

// Sonucu almak ve kullanmak için:
let sonuç = tasKagitMakas('makas');
console.log(sonuç);
