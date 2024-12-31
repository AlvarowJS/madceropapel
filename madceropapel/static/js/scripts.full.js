/*
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
*/
$(function () {
    // "use strict";
    $(".preloader").fadeOut();
});

function ajustarTablas() {
    // $($.fn.dataTable.tables(true)).DataTable().scroller.measure();
    setTimeout(function () {
        $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
        $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
    }, 200);
}

$('body').on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
    ajustarTablas();
});

!function (a) {
    a.fn.datepicker.dates.es = {
        days: ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
        daysShort: ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"],
        daysMin: ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"],
        months: ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        monthsShort: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
        today: "Hoy",
        monthsTitle: "Meses",
        clear: "Borrar",
        weekStart: 1,
        format: "dd/mm/yyyy"
    }
}(jQuery);

$('html').on('change', '.custom-file-input', function () {
    let miFile = $(this).val();
    let _error = false;
    if ($(this).val() !== '') {
        if ($(this).data("extensions")) {
            let extensions = $(this).data("extensions");
            let ext = $(this).val().split('.').pop();
            if (extensions.indexOf(ext) === -1) {
                // $(this).val('');
                // colocar el error de bootstrap al control
                _error = true;
            }
        }
        if (!_error && $(this).data("maxsize")) {
            let maxsize = parseInt($(this).data("maxsize"));
            if ($(this)[0].files[0].size > maxsize) {
                // $(this).val('');
                // colocar el error de boostrap al control
                _error = true;
            }
        }
    }
    if (!_error) {
        $(this).next('.custom-file-label')
            .addClass("con-archivo")
            .html(document.getElementById($(this).prop("id")).files[0].name);
        $(this).next('.custom-file-label.con-archivo::before').on("click", function () {
            console.log($(this));
        })
    } else {
        $(this).next('.custom-file-label')
            .removeClass("con-archivo")
            .html("");
    }

});

