// (c)2026 Jon Robinson. All Rights Reserved.

// Stops a scroll that starts on the 2D graph from selecting a glass.
//
// The 2D figure has dragmode false (callback_helpers.populate_graph_ts_tv), so plotly leaves
// touch drags to the browser and a finger on the graph scrolls the page. But with no drag
// mode plotly does not watch the finger move either: when it lifts, plotly takes the touch
// for a tap and looks for a point where the touch began, in a graph that has since scrolled
// away from under it. In the crowded scatter it usually finds one, and the selection jumps
// to a glass the user never touched.
//
// plotly decides between "drag" and "click" from the graph div's _dragged flag when the
// touch ends, in a listener on document. This listener is on document too but in the
// capture phase, so it runs first and sets the flag when the finger moved or the page
// scrolled. _dragged is internal to plotly: if a plotly upgrade stops using it, this turns
// into a no-op and the stray selections come back, nothing worse. plotly resets the flag
// itself at the end of every touch.
(function () {
    var SLOP = 10;  // px a finger may wander and still be a tap
    var start = null;

    document.addEventListener('touchstart', function (e) {
        if (e.touches.length !== 1) {
            start = null;
            return;
        }
        var touch = e.touches[0];
        start = {x: touch.clientX, y: touch.clientY, scrollX: window.scrollX, scrollY: window.scrollY};
    }, {capture: true, passive: true});

    document.addEventListener('touchend', function (e) {
        var from = start;
        start = null;
        if (!from || !e.changedTouches.length || !e.target || !e.target.closest) {
            return;
        }

        // Only the drag layer of a 2D plot: the 3D scenes handle their own touches
        var graph = e.target.closest('.draglayer') && e.target.closest('.js-plotly-plot');
        if (!graph) {
            return;
        }

        var touch = e.changedTouches[0];
        var moved = Math.abs(touch.clientX - from.x) > SLOP || Math.abs(touch.clientY - from.y) > SLOP;
        var scrolled = Math.abs(window.scrollX - from.scrollX) > 1 || Math.abs(window.scrollY - from.scrollY) > 1;
        if (moved || scrolled) {
            graph._dragged = true;
        }
    }, {capture: true, passive: true});
})();
