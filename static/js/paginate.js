class Paginate {

    constructor(element = ".object", opts = {}) {

        this.element = element
        this.options = $.extend({}, {
            page: 1,
            number_of_pages: 1,
            page_size: 10,
        }, opts)

        console.log("initalizing pagination with options", this.options)

        if (!(element && $(element).length))
            return

        this.init()
        this.filter = new Filter(element, $.extend({}, {
            paginate: this
        }, opts))
    }

    init() {
        console.log("initializing pagination for", this.element)

        if (!$(".paginate").length) {
            console.log("creating pagination elements...")

            $(this.element).first().parent().append(
                '<div class="flex center row mobile-row" style="width: 100%">' +
                '<div class="paginate flex row mobile-row space">' +
                '<div class="paginate-back"></div>' +
                '<div class="paginate-pages flex row mobile-row"></div>' +
                '<div class="paginate-next"></div>' +
                '</div></div>'
            )
        }

        // event binders

        $(document).on("click", ".paginate-next", function () {
            this.options.page = Math.min(this.options.number_of_pages, this.options.page + 1)
            this.filter.update()
        }.bind(this))

        $(document).on("click", ".paginate-back", function () {
            this.options.page = Math.max(0, this.options.page - 1)
            this.filter.update()
        }.bind(this))

        $(document).on("click", ".paginate-page", function (e) {
            if ($(e.target).data("page")) {
                this.options.page = +$(e.target).data("page")
                this.filter.update()
            }
        }.bind(this))
    }

    update(scroll = true) {
        console.log("updating pagination")
        this.options.number_of_pages = Math.ceil($(this.element + ":visible").length / this.options.page_size)

        $(this.element + ":visible").each(function (k, v) {
            $(v).hide()
            if (k >= this.options.page_size * (this.options.page - 1) && k < this.options.page_size * this.options.page)
                $(v).show()
        }.bind(this))

        $(".paginate-page").remove()
        for (var i = 1; i <= this.options.number_of_pages; i++) {
            var obj = $("<div/>").addClass("paginate-page").text(i)
            if (i == this.options.page) obj.addClass("active")
            else obj.data("page", i)

            $(".paginate-pages").append(obj)
        }

        $(".paginate-back, .paginate-next").removeClass("deactivated")

        if (this.options.page == this.options.number_of_pages) $(".paginate-next").addClass("deactivated")
        if (this.options.page == 1) $(".paginate-back").addClass("deactivated")

        if (scroll && this.filter.options.filter_sources.search) $(this.filter.options.filter_sources.search).animateScroll()
        else if (scroll) $(this.element).first().parent().animateScroll()
    }

}

class Filter {

    constructor(element = ".object", opts = {}) {

        this.element = element
        this.options = $.extend({}, {
            paginate: null,
            objects_filter: ".objects-filter",
            objects_filter_header: ".objects-filter-header",
            objects_filter_group: ".objects-filter-group",
            objects_filter_title: ".objects-filter h5",
            search_fields: ["value"],
            hide_on_mobile: true,
            filter_sources: {
                filter: ".filter",
                search: "#search"
            }
        }, opts)

        console.log("received options", opts, this.options)

        if (!(element && $(element).length))
            return

        this.init()
    }

    init() {
        console.log("initializing filters for", this.element)

        // event listeners
        $(document).on("click", this.options.objects_filter_header, function (e) {
            $(e.target).closest(this.options.objects_filter_group).toggleClass("open")
        }.bind(this))

        $(document).on("click", this.options.objects_filter_title, function (e) {
            $(e.target).closest(this.options.objects_filter).toggleClass("open")
        }.bind(this))

        $(document).on("input", Object.values(this.options.filter_sources).join(","), function () {
            this.update()
        }.bind(this))

        // hide on mobile
        if (this.options.hide_on_mobile) {
            this.old_width = null
            $(window).on("resize", function (e) {
                if ($(window).width() !== this.old_width) {
                    this.old_width = $(window).width()
                    if (this.old_width <= 768 && this.options.objects_filter)
                        $(this.options.objects_filter).removeClass("open")
                }

            }.bind(this)).trigger("resize")
        }

        this.update(false)
    }

    update(scroll = true) {
        console.log("updating filters", this.options)
        $(this.element).show()

        // filters
        if (this.options.filter_sources.filter) {
            var filters = {}
            $(this.options.filter_sources.filter).each(function (k, e) {
                if ($(e).prop("checked")) {
                    if (filters[$(e).attr("name")])
                        filters[$(e).attr("name")].push(this.get(e))
                    else if (typeof this.get(e) === "object" || typeof this.get(e) === "array")
                        filters[$(e).attr("name")] = this.get(e)
                    else
                        filters[$(e).attr("name")] = [this.get(e)]
                }
            }.bind(this))

            console.log("filters", filters)

            if (Object.keys(filters).length) {
                for (const key in filters) {
                    $(this.element).each(function (k, e) {
                        e = $(e)
                        console.log(filters[key], typeof filters[key])
                        // search for any matches
                        var includes = filters[key].some(v => e.data(key) && e.data(key).includes(v))
                        if (!includes) e.hide()
                    })
                }
            }
        }

        // search
        if (this.options.filter_sources.search) {
            var search = $(this.options.filter_sources.search).val()
            if (search) {
                search = search.toLowerCase()
                $(this.element).each(function (k, e) {
                    e = $(e)
                    // search for any matches
                    var includes = this.options.search_fields.some(v => e.data(v) && e.data(v).toLowerCase().includes(search))
                    if (!includes) e.hide()
                }.bind(this))
            }
        }

        if (this.options.paginate) {
            console.log("updating pagination from filter")
            this.options.paginate.update(scroll)
        }
    }

    get(element) {
        console.log(typeof element)
        element = $(element)

        if (element.data("value"))
            return element.data("value")

        return element.val()
    }
}