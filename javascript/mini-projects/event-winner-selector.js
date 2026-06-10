const eventList = Array.from(
    { length: 100 },
    (_, i) => `user${i + 1}`
);
function getWinner(eventList){
    const winners = [];
    winners.push(eventList[0]);
    winners.push(eventList[eventList.length - 1]);
    return winners;
}
console.log(getWinner(eventList));