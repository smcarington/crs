$(document).ready(function() {

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
            return cookieValue;
    }

    // Make all ajax requests include a header with the CSRF token
    var csrftoken = getCookie('csrftoken'); 

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
    
    // Select all items whose class begins with "mathrender". These could have LaTeX code.
    // Pass them to autorender
    $('.mathrender').each( function () {
        renderMathInElement( $(this)[0] );
    });

    // Adds datetimepickers

    jQuery('#id_expires').datetimepicker(
            { format:'Y-m-d H:i',
            });
    jQuery('#id_live').datetimepicker(
            { format:'Y-m-d H:i',
            });
    
    if ($("#id_q_type option:selected").text() != "Multiple Choice") {
        $("#id_mc_choices").prop("disabled", true);
    }

    $("#id_q_type").change( function() {
        if ($(this).find("option:selected").text() == 'Multiple Choice') {
            $("#id_mc_choices").prop('disabled', false);
        } else {
            $("#id_mc_choices").prop('disabled', true);
        }
    });


});
