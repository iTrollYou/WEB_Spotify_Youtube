function AJAX() {
    nocache = "nocache=" + Math.random() * 1000000; // Para evitar que el navegador guarde en memoría la respuesta HTTP
    var request = new XMLHttpRequest(); //Objeto AJAX para realizar la petición

    request.onreadystatechange = function () {
        if (request.readyState == 4) { // XMLHttpReques status: 4 significado : request finished and response is ready
            if (request.status == 200) { // estadorespuesta HTTP
                if (request.responseText != null) { // si la respuesta tiene contenido ....
                    var jsonObj = JSON.parse(request.responseText); // El contenido de la respuesta HTTP se recibe como(request.responseText)
                    // y convierte a JSON (JSON.parse())
                    document.getElementsByClassName("tweet1")[0].innerHTML = jsonObj[0].text;
                    document.getElementsByClassName("tweet1_img")[0].src = jsonObj[0].user.profile_image_url;
                    document.getElementsByClassName("tweet2")[0].innerHTML = jsonObj[1].text;
                    document.getElementsByClassName("tweet2_img")[0].src = jsonObj[1].user.profile_image_url;
                    document.getElementsByClassName("tweet3")[0].innerHTML = jsonObj[2].text;
                    document.getElementsByClassName("tweet3_img")[0].src = jsonObj[2].user.profile_image_url;
                }
            }
        }
    };

    request.open("GET", "/RefreshLast3Tweets?" + nocache, true); // preparar petición HTTP
    request.send(null); // Enviar petición HTTP
    setTimeout("AJAX()", 60000); // Se llama la la función AJAX cada 60 segundos.

}