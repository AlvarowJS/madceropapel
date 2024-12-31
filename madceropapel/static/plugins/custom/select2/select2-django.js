(function ($) {
    var init = function ($element, options) {
        var settings = $.extend({
            minimumResultsForSearch: ($element.data("minimum-results-for-search") === "Infinity" ? -1 : 0),
            width: $element.data("width") || "100%"
        }, options);
        $element.select2(settings);
    };

    var initHeavy = function ($element, options) {
        let $dependentFields0 = $element.data('select2-dependent-fields');
        if ($dependentFields0 !== undefined) {
            $dependentFields0 = $dependentFields0.trim().split(/\s+/);
            $.each($dependentFields0, function (i, dependentField) {
                let objdep = $('[name="' + dependentField + '"]');
                objdep.on("change", function () {
                    $element.val(null).trigger("change");
                    $element.empty();
                });
            });
        }
        var settings = $.extend({
            dropdownParent: $element.parent() || null,
            placeholder: "",
            allowClear: $element.data("allow-clear"),
            minimumResultsForSearch: ($element.data("minimum-results-for-search") === "Infinity" ? -1 : 0),
            ajax: {
                delay: 1000,
                data: function (params) {
                    var result = {
                        term: params.term,
                        page: params.page,
                        field_id: $element.data('field_id')
                    };
                    if ($element.data('ajax--param1')) result["param1"] = $element.data('ajax--param1');
                    if ($element.data('ajax--param2')) result["param2"] = $element.data('ajax--param2');
                    if ($element.data('ajax--param3')) result["param3"] = $element.data('ajax--param3');

                    $dependentFields = $element.data('select2-dependent-fields');
                    if ($dependentFields !== undefined) {
                        $dependentFields = $dependentFields.trim().split(/\s+/);
                        $.each($dependentFields, function (i, dependentField) {
                            objdep = $('select[name="' + dependentField + '"]');
                            valdep = objdep.val();
                            if (!valdep) valdep = 0;
                            result[dependentField] = valdep;
                        })
                    }
                    return result
                },
                processResults: function (data, page) {
                    return {
                        results: $.map(data.results, function (obj) {
                            return obj;
                        }),
                        pagination: {
                            more: data.more
                        }
                    }
                }
            },
            templateResult: function (state) {
                return $.parseHTML(state.text);
            },
            templateSelection: function (state) {
                return $.parseHTML(state.text);
            },
        }, options);

        $element.select2(settings);

        if ($element.select2("data").length > 0) {
            let datasel = $element.select2("data")[0];
            let data = {
                "field_id": $element.data("field_id"),
                "sel_id": datasel.id
            }
            let depfields = $element.data("select2-dependent-fields");
            if (depfields) {
                depfields = depfields.trim().split(/\s+/);
                $.each(depfields, function (i, dependentField) {
                    data[dependentField] = $('select[name="' + dependentField + '"]').val();
                });
            }
            $.ajax({
                type: $element.data("ajax--type"),
                url: $element.data("ajax--url"),
                data: data,
                dataType: 'json'
            }).then(function (datar) {
                if (datar.results.length > 0) {
                    datar.results.forEach(elemento => {
                        if (String(datasel.id) === String(elemento.id)) {
                            Object.entries(elemento).forEach(([key, value]) => {
                                if (key !== "text" && key !== "id") {
                                    eval("datasel." + key + " = value;");
                                }
                            });
                        }
                    });
                }
            });
        }
    };

    $.fn.select2.defaults.set('language', 'es');
    // $.fn.select2.defaults.set('width', '100%');
    $.fn.select2.defaults.set('dropdownAutoWidth', true);

    $.fn.djangoSelect2 = function (options) {
        var settings = $.extend({}, options);
        $.each(this, function (i, element) {
            var $element = $(element);
            if ($element.hasClass('django-select2-heavy')) {
                initHeavy($element, settings)
            } else {
                init($element, settings)
            }
            $element.on('select2:selectfirst', function (e, withnull) {
                let data = {
                    "field_id": $element.data("field_id")
                }
                let depfields = $element.data("select2-dependent-fields");
                if (depfields) {
                    depfields = depfields.trim().split(/\s+/);
                    $.each(depfields, function (i, dependentField) {
                        data[dependentField] = $('select[name="' + dependentField + '"]').val();
                    });
                }
                $.ajax({
                    type: $element.data("ajax--type"),
                    url: $element.data("ajax--url"),
                    data: data,
                    dataType: 'json'
                }).then(function (datar) {
                    if (datar.results.length > 0) {
                        let option = new Option(
                            datar.results[0].text,
                            datar.results[0].id,
                            true,
                            true
                        );
                        $element.append(option).trigger('change');
                        let data = $element.select2('data')[0];
                        Object.entries(datar.results[0]).forEach(([key, value]) => {
                            if (key !== "text" && key !== "id") {
                                eval("data." + key + " = value;");
                            }
                        });
                        $element.trigger("change");
                    } else {
                        if (withnull) $element.empty().trigger("change");
                    }
                });
            }).on('select2:sel_id', function (e, id, cambiar) {
                let data = {
                    "field_id": $element.data("field_id"),
                    "sel_id": id
                }
                let depfields = $element.data("select2-dependent-fields");
                if (depfields) {
                    depfields = depfields.trim().split(/\s+/);
                    $.each(depfields, function (i, dependentField) {
                        data[dependentField] = $('select[name="' + dependentField + '"]').val();
                    });
                }
                $.ajax({
                    type: $element.data("ajax--type"),
                    url: $element.data("ajax--url"),
                    data: data,
                    dataType: 'json'
                }).then(function (datar) {
                    // $element.find("option").remove();
                    if (datar.results.length > 0) {
                        let option = new Option(
                            datar.results[0].text,
                            datar.results[0].id,
                            true,
                            true
                        );
                        $element.append(option); //.trigger('change');
                        let data = $element.select2('data')[0];
                        Object.entries(datar.results[0]).forEach(([key, value]) => {
                            if (key !== "text" && key !== "id") {
                                eval("data." + key + " = value;");
                            }
                        });
                        // if (typeof cambiar !== "undefined") {
                        //     console.log("triger");
                        //     $element.trigger("change");
                        // }
                        // setTimeout(function () {
                        //    $element.trigger("change");
                        // }, 200);
                        //
                    }
                });
            });
        });
        return this
    };

    $(function () {
        $('.django-select2').djangoSelect2();
    })
}(this.jQuery));