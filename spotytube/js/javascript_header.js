$(document).ready(function () {/*Cuando el documento esta listo carga la funcion*/
    $(window).scroll(function () { /*Cuando hacemos scroll carga la funcion*/
        if ($(this).scrollTop() > 0) {
            $('header').addClass('header2');
        } else {
            $('header').removeClass('header2');
        }
    });
});
