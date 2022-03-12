function faceCheck(n) {$.get('/person', 
	function(data) {
		if (data == 'oscar'){
			setTimeout(() => {faceCheck(5000)}, n);
		}else{
			var url = "/user/" + data
			document.body.style.animation = 'fadeOutAnimation ease 3s'
			setTimeout(() => {window.location.replace(url)}, 2900);
			
		}
    });
}



function resize_to_fit(n) {
	  document.getElementById("text").style.fontSize = (n) + "vw";

	  if (document.getElementById("text").offsetHeight >= document.getElementById("outer").offsetHeight) {
		resize_to_fit(n-1);
	  }
}

function showTime(){
    var date = new Date();
    var h = date.getHours().toLocaleString(undefined, {minimumIntegerDigits: 2}); // 0 - 23
    var m = date.getMinutes().toLocaleString(undefined, {minimumIntegerDigits: 2}); // 0 - 59
    var s = date.getSeconds().toLocaleString(undefined, {minimumIntegerDigits: 2}); // 0 - 59

    var time = h + ":" + m + ":" + s;
    document.getElementById("MyClockDisplay").innerText = time;
    document.getElementById("MyClockDisplay").textContent = time;
    
    setTimeout(showTime, 1000);
}

