var currentPalette = null
var currentPaletteID = null

function fillPalette(palette) {
    currentPalette = palette.map(e => e.formats.hex)

    $(".generator .controls .save").removeClass("saved")
    $(".generator .colors .color").remove()

    $.each(palette, function (k, v) {
        $("<div/>", { "class": "color flex-item grow flex column mobile-row mobile-reverse space " + (v.lightness > 70 ? "dark" : "") })
            .css("background-color", `#${v.formats.hex}`)
            .data("color", v.formats.hex)
            .append(
                $("<div/>", { "class": "color-fav" }))
            .append(
                $("<div/>")
                    .append(
                        $("<div/>", { "class": "color-hex" }).text(v.formats.hex))
                    .append(
                        $("<div/>", { "class": "color-name" }).text(v.name)))
            .insertBefore($(".generator .palette-library"))
    })
}

function getPalette() {
    let options = $("#generator-form").serialize()
    ajax("/api/generate", {
        data: options,
        returnData: function (data) {
            currentPaletteID = null
            fillPalette(data.palette)
        }
    })
}

$(function () {

    // listen for space bar
    $(document).on("keypress", function (e) {
        if (e.keyCode == 32) { // space bar
            e.preventDefault() // prevent scrolling
            getPalette()
        }
    })

    // listen for generate button
    $(document).on("click", ".generate", getPalette)

    // listen for my palette
    $(document).on("click", ".generator .controls .my-palettes", function (e) {
        e.preventDefault() // prevent going to #

        $(".generator .palette-library").toggleClass("open")

        if ($(".generator .palette-library").hasClass("open")) {
            // load saved palettes
            ajax("/api/palettes", {
                method: "GET",
                returnData: function (data) {
                    $(".generator .palette-library .palettes .palette").remove()

                    $.each(data.palettes, function (k, v) {
                        console.log(k)
                        let palette = $("<div/>", { "class": "palette flex row space mobile-row flex-item " + (k > 0 ? "flex-margin-small" : "") })
                            .data("id", v.id)
                        $.each(v.colors, function (_, c) {
                            $("<div/>", { "class": "color flex-item grow " + (c.lightness > 70 ? "dark" : "") })
                                .css("background-color", `#${c.hex}`)
                                .append(
                                    $("<div/>", { "class": "color-hex" }).text(c.hex))
                                .appendTo(palette)
                        })

                        $(".generator .palette-library .palettes").append(palette)
                    })
                },
                onError: function (data) {
                    console.error(data)
                }
            })
        }

    })

    // listen for save
    $(document).on("click", ".generator .controls .save", function (e) {
        e.preventDefault()

        if (!$(this).hasClass("saved") && currentPalette) {
            var this_ = $(this)
            // save
            ajax("/api/palette", {
                data: {
                    palette: currentPalette
                },
                returnData: function (data) {
                    currentPaletteID = data.palette_id
                    this_.addClass("saved")
                },
                onError: function (data) {
                    if (data.status == 401) {
                        alert("You need to log in to save palettes")
                    } else {
                        console.error(data)
                    }
                }
            })
        } else if ($(this).hasClass("saved") && currentPaletteID) {
            var this_ = $(this)
            // remove
            ajax(`/api/palette/${currentPaletteID}/delete`, {
                method: "GET",
                returnData: function (data) {
                    this_.removeClass("saved")
                },
                onError: function (data) {
                    console.error(data)
                }
            })
        }
    })

    // listen for color save
    $(document).on("click", ".generator > .colors > .color > .color-fav", function (e) {
        e.preventDefault()

        console.log($(this).parent(), $(this).parent().data("color_id"))

        if (!$(this).hasClass("saved")) {
            var this_ = $(this)
            // save
            ajax("/api/color", {
                data: {
                    color: this_.parent().data("color")
                },
                returnData: function (data) {
                    this_.parent().data("color_id", data.color_id)
                    this_.addClass("saved")
                },
                onError: function (data) {
                    if (data.status == 401) {
                        alert("You need to log in to save colors")
                    } else {
                        console.error(data)
                    }
                }
            })
        } else if ($(this).hasClass("saved") && $(this).parent().data("color_id")) {
            var this_ = $(this)
            // remove
            ajax(`/api/color/${$(this).parent().data("color_id")}/delete`, {
                method: "GET",
                returnData: function (data) {
                    this_.removeClass("saved")
                },
                onError: function (data) {
                    console.error(data)
                }
            })
        }
    })

    // listen for upload to create
    $(document).on("click", ".generator .controls .create-from-image", function (e) {
        e.preventDefault()

        $(".upload").fadeIn()
    })

    // listen for search with palette
    $(document).on("click", ".generator .controls .search-with-palette", function (e) {
        e.preventDefault()

        // create URL
        let url = new URL(location.origin + "/search")
        url.searchParams.append("p", currentPalette)

        location.href = url.href
    })

    $(document).on("click", ".upload .upload-background", function (e) {
        e.preventDefault()
        if (
            (!$(e.target).hasClass("popup") && !$(e.target).parents(".popup").length)
            || $(e.target).hasClass("close")
        ) {
            $(".upload").fadeOut()
        }
    })

    // listen for options (mobile)
    $(document).on("click", ".generator .generator-menu-mobile .options", function () {
        $(this).siblings(".controls").toggleClass("open")
    })

    getPalette()

})