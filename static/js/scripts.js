// animate scroll to element
jQuery.fn.animateScroll = function (speed = 600, margin = 32) {
    $("html, body").animate({ scrollTop: $(this).offset().top - margin }, speed)
}

$(function () {
    // indent animation
    setTimeout(function () {
        $("[data-indent]").each(function () {
            let indent_by = $(this).data("indent") * 64
            $(this).animate({
                paddingLeft: indent_by
            }, 1000)
        })
    }, 250)

    // button animation
    $(document).on("mousedown touchstart", ".button", function () { $(this).addClass("click") })
    $(document).on("mouseup touchend", () => { $(".button").removeClass("click") })

    // navigation mobile
    $(document).on("click", ".burger", function () {
        $(this).closest(".nav-mobile").toggleClass("open")
    })

    // switch nav bar
    $(window).on("scroll", function () {
        let scroll = $(window).scrollTop()
        if (scroll > 0) {
            $(".nav-desktop").addClass("scrolled")
        } else {
            $(".nav-desktop").removeClass("scrolled")
        }
    })

    // copy hex codes
    $(document).on("click", ".color-hex", function (e) {
        let this_ = $(this)
        navigator.clipboard.writeText(this_.text()).then(
            function () {
                this_.addClass("copied")
                setTimeout(function () {
                    this_.removeClass("copied")
                }, 1000)
            },
            function (err) {
                console.error(err)
                this_.addClass("error")
                setTimeout(function () {
                    this_.removeClass("error")
                }, 1000)
            }
        )
    })

    $(document).on("keypress", function (e) {
        if (e.keyCode == 13) {
            $(".enter-to-click").trigger("click")
        }
    })

    // file upload
    if (testAdvancedUpload()) setAdvancedUpload()

    $(document).on("input change", ".file-upload input[type=file]", function () {
        var files = this.files

        if (files && validateFiles(files)) {
            $(this).closest(".file-upload").addClass("has-file")
            if ($(this).closest(".file-upload").data("preview")) {
                $("." + $(this).closest(".file-upload").data("preview")).attr("src", window.URL.createObjectURL(files[0]))
                $("." + $(this).closest(".file-upload").data("preview")).addClass("active")
            }

            if ($(this).closest(".file-upload").hasClass("auto-upload")) {
                upload(files[0], uploadURL, callback)
            }
        } else {
            $(this).closest(".file-upload").removeClass("has-file")
            $("." + $(this).closest(".file-upload").data("preview")).attr("src", "")
            $("." + $(this).closest(".file-upload").data("preview")).removeClass("active")
        }
    })
})

// default ajax request with error handling
function ajax(url, options = {}) {
    // set default values
    var def = {
        data: null,
        form: null,
        returnData: null,
        onError: null,
        displayLoading: true,

        async: true,
        cache: false,
        complete: null,
        contentType: "application/x-www-form-urlencoded; charset=UTF-8",
        dataType: "json",
        processData: true,
        method: "POST"
    }

    for (const k in def)
        if (!options.hasOwnProperty(k))
            options[k] = def[k]

    if (options.form && options.displayLoading) options.form.addClass("loading")

    $.ajax({
        url: url,
        method: options.method,
        data: options.data,
        cache: options.cache,
        dataType: options.dataType,
        async: options.async,
        contentType: options.contentType,
        processData: options.processData

    }).done(function (data) {
        console.log(data)
        if (options.dataType == "json") {
            if (options.returnData) {
                options.returnData(data)
            }
        }

    }).fail(function (data) {
        if (options.onError) {
            options.onError(data)
        } else {
            console.log("error in request to", url)
            console.log("parameters", options)
            console.error(data)
        }

    }).always(function (data) {
        if (options.form) options.form.removeClass("loading")
        if (options.complete) options.complete(data)
    })
}

// advanced upload

function testAdvancedUpload() {
    var div = document.createElement("div")
    return ("ondrag" in div)
}

function setAdvancedUpload() {
    $(".file-upload").addClass("advanced")

    var droppedFiles = false

    $(".file-upload")
        .on("drag dragstart dragend dragover dragenter dragleave drop", function (e) {
            e.preventDefault()
            e.stopPropagation()
        })
        .on("dragover dragenter", function () {
            $(".file-upload").addClass("is-dragover")
        })
        .on("dragleave dragend drop", function () {
            $(".file-upload").removeClass("is-dragover")
        })
        .on("drop", function (e) {
            droppedFiles = e.originalEvent.dataTransfer.files
            $(this).find("input[type=file]").get(0).files = droppedFiles
            $(this).find("input[type=file]").trigger("input")

            if (droppedFiles && validateFiles(droppedFiles)) {
                if ($(this).hasClass("auto-upload")) {
                    upload(droppedFiles[0], uploadURL, callback)
                }
            }
        })
}

// file actions

function upload(file, url = null, returnData = null) {

    if ($(".file-upload").hasClass("is-uploading")) return

    $(".file-upload").removeClass("is-error")
    $(".file-upload").removeClass("is-success")
    $(".file-upload").addClass("is-uploading loading")

    var formData = new FormData()
    formData.append("file", file)

    console.log(url)

    $.ajax({
        url: url,
        type: "post",
        data: formData,
        contentType: false,
        processData: false,
        complete: function () {
            $(".file-upload").removeClass("is-uploading loading")
            setTimeout(function () {
                $(".file-upload").removeClass("is-success")
                $(".file-upload").removeClass("is-error")
            }, 2000)
        },
        success: function (data) {
            console.log(data)
            if (returnData) returnData(data)
        },
        error: function (err) {
            $(".file-upload").addClass("is-error")
            $(".file-upload__error span").text(err.responseJSON.message)
            console.error(err)
        },
        done: function (msg) {
            console.log(msg)
        }
    })
}

function validateFiles(files) {

    $(".file-upload").addClass("is-error")
    setTimeout(function () { $(".file-upload").removeClass("is-error") }, 2000)
    $(".file-upload__info").text("")

    if (files && files.length) {
        if (files.length > 1) {
            $(".file-upload__error span").text("You can only upload one file")
            return false
        }
        else if (files[0].size > 8388608) {
            $(".file-upload__error span").text("File must be smaller than 8MB")
            return false
        }
        else if (!["image/jpeg", "image/jpg", "image/png", "image/gif"].includes(files[0].type)) {
            $(".file-upload__error span").text("Filetype " + files[0].type + " not supported")
            return false
        }

        $(".file-upload__info").text("File OK")
        $(".file-upload").removeClass("is-error")

        setTimeout(() => {
            $(".file-upload__info").text("")
        }, 2000)

        return true
    }

}