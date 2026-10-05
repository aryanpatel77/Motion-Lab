// Motion Lab — After Effects runtime.
// Builds an editable comp from a scene description (see tools/ae/scene.py).
// Generated files append:  MotionLab.build(<scene json>);
// Tested against AE 2020+ APIs. Everything is wrapped so one unsupported feature never kills the build.

var MotionLab = (function () {
  var WARN = [];
  function warn(m) { for (var i = 0; i < WARN.length; i++) if (WARN[i] === m) return; WARN.push(m); }

  function easeKeys(prop, ease, dims) {
    if (ease === "linear" || prop.numKeys < 2) return;
    if (ease === "hold") {
      for (var h = 1; h <= prop.numKeys; h++)
        try { prop.setInterpolationTypeAtKey(h, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD); } catch (e) { warn("hold keys"); }
      return;
    }
    var inf = 70;
    for (var k = 1; k <= prop.numKeys; k++) {
      var easeIn = [], easeOut = [];
      for (var d = 0; d < dims; d++) {
        easeIn.push(new KeyframeEase(0, (ease === "out" && k === 1) ? 0.1 : inf));
        easeOut.push(new KeyframeEase(0, (ease === "in" && k === prop.numKeys) ? 0.1 : inf));
      }
      try { prop.setTemporalEaseAtKey(k, easeIn, easeOut); } catch (e) { warn("temporal ease"); }
    }
  }

  function dimsOf(v) { return (v instanceof Array) ? v.length : 1; }

  function applyProp(layer, name, spec, ctx) {
    var t = layer.property("ADBE Transform Group");
    var map = { position: "ADBE Position", opacity: "ADBE Opacity", scale: "ADBE Scale",
                rotation: "ADBE Rotate Z", anchor: "ADBE Anchor Point" };
    var prop;
    if (name === "sourceText") prop = layer.property("ADBE Text Properties").property("ADBE Text Document");
    else if (map[name]) prop = t.property(map[name]);
    else if (name === "trimStart") prop = ctx.trim ? ctx.trim.property("ADBE Vector Trim Start") : null;
    else if (name === "trimEnd") prop = ctx.trim ? ctx.trim.property("ADBE Vector Trim End") : null;
    else if (name === "fillColor" && ctx.fill) prop = ctx.fill.property("ADBE Vector Fill Color");
    else if (name === "strokeWidth" && ctx.stroke) prop = ctx.stroke.property("ADBE Vector Stroke Width");
    if (!prop) { warn("unsupported property: " + name); return; }

    var keys = spec.keys;
    for (var i = 0; i < keys.length; i++) {
      var time = keys[i][0], val = keys[i][1];
      if (name === "sourceText") {
        var doc = prop.value; doc.text = String(val); prop.setValueAtTime(time, doc);
      } else if (name === "position" && ctx.offset) {
        prop.setValueAtTime(time, [val[0] + ctx.offset[0], val[1] + ctx.offset[1]]);
      } else {
        prop.setValueAtTime(time, val);
      }
    }
    if (keys.length === 1) {                       // single key = a static value, no animation
      try { prop.setValue(prop.valueAtTime(keys[0][0], false)); prop.removeKey(1); } catch (e) {}
      return;
    }
    easeKeys(prop, name === "sourceText" ? "hold" : spec.ease, dimsOf(keys[0][1]));
  }

  function rectShape(x, y, w, h) {
    var s = new Shape();
    s.vertices = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
    s.inTangents = [[0, 0], [0, 0], [0, 0], [0, 0]];
    s.outTangents = [[0, 0], [0, 0], [0, 0], [0, 0]];
    s.closed = true;
    return s;
  }

  function addMask(layer, spec) {
    try {
      var m = layer.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
      if (spec.invert) m.inverted = true;
      var prop = m.property("ADBE Mask Shape");
      for (var i = 0; i < spec.keys.length; i++) {
        var r = spec.keys[i][1];
        prop.setValueAtTime(spec.keys[i][0], rectShape(r[0], r[1], r[2], r[3]));
      }
      if (spec.keys.length === 1) { try { prop.setValue(prop.valueAtTime(spec.keys[0][0], false)); prop.removeKey(1); } catch (e) {} }
      else easeKeys(prop, spec.ease, 1);
    } catch (e) { warn("masks: " + e.toString()); }
  }

  function addEffects(layer, list) {
    for (var i = 0; i < (list || []).length; i++) {
      var e = list[i], p = e.params || {};
      try {
        if (e.name === "glow") {
          var g = layer.property("ADBE Effect Parade").addProperty("ADBE Glo2");
          if (p.radius) g.property("ADBE Glo2-0003").setValue(p.radius);
          if (p.threshold) g.property("ADBE Glo2-0002").setValue(p.threshold);
          if (p.intensity) g.property("ADBE Glo2-0004").setValue(p.intensity);
          if (p.colorA) {                                          // Glow Colors: A & B
            try { g.property("Glow Colors").setValue(2); g.property("Color A").setValue(p.colorA.concat([1]));
                  g.property("Color B").setValue((p.colorB || p.colorA).concat([1])); }
            catch (ec) { warn("glow colours not set on '" + layer.name + "' — set Glow Colors to A & B by hand"); }
          }
        } else if (e.name === "ramp") {
          var r = layer.property("ADBE Effect Parade").addProperty("ADBE Ramp");
          r.property("ADBE Ramp-0001").setValue(p.start);
          r.property("ADBE Ramp-0002").setValue(p.startColor.concat([1]));
          r.property("ADBE Ramp-0003").setValue(p.end);
          r.property("ADBE Ramp-0004").setValue(p.endColor.concat([1]));
        } else if (e.name === "blur") {
          var names = ["ADBE Gaussian Blur 2", "ADBE Gaussian Blur", "ADBE Fast Blur", "ADBE Box Blur2"], done = false;
          for (var bi = 0; bi < names.length && !done; bi++) {
            try {
              var b = layer.property("ADBE Effect Parade").addProperty(names[bi]);
              var amt = p.amount || 20;
              try { b.property(1).setValue(amt); } catch (e3) { b.property("Blurriness").setValue(amt); }
              for (var pi = 2; pi <= 4; pi++) {                       // repeat edge pixels, where present
                try { if (b.property(pi).propertyValueType === PropertyValueType.NO_VALUE) continue;
                      if (typeof b.property(pi).value === "boolean") b.property(pi).setValue(true); } catch (e4) {}
              }
              done = true;
            } catch (e2) {}
          }
          if (!done) { layer.enabled = false; warn("blur unavailable — '" + layer.name + "' hidden instead of drawn hard"); }
        } else if (e.name === "tint") {
          var t = layer.property("ADBE Effect Parade").addProperty("ADBE Tint");
          t.property("ADBE Tint-0001").setValue(p.black.concat([1]));
          t.property("ADBE Tint-0002").setValue(p.white.concat([1]));
        }
      } catch (err) { warn("effect " + e.name + ": " + err.toString()); }
    }
  }

  function setText(layer, t) {
    var prop = layer.property("ADBE Text Properties").property("ADBE Text Document");
    var doc = prop.value;
    doc.text = t.value;
    doc.fontSize = t.size;
    doc.fillColor = t.color;
    doc.applyFill = true;
    doc.applyStroke = false;
    doc.justification = t.justify === "center" ? ParagraphJustification.CENTER_JUSTIFY : ParagraphJustification.LEFT_JUSTIFY;
    if (t.tracking) { try { doc.tracking = t.tracking; } catch (e) { warn("tracking"); } }
    if (t.ps) {                                                  // PostScript name is the reliable way to pick a font
      try { doc.font = t.ps; } catch (e) { warn("font '" + t.ps + "' not set — pick it in the Character panel"); }
    } else if (t.font) {
      try { doc.fontFamily = t.font; if (t.italic) doc.fontStyle = "Italic"; }
      catch (e) { try { doc.font = t.font; } catch (e2) { warn("font '" + t.font + "' not set — pick it in the Character panel"); } }
    }
    if (t.leading) { try { doc.leading = t.leading; doc.autoLeading = false; } catch (e) { warn("leading"); } }
    prop.setValue(doc);
    try {                                                     // did AE actually get the font, or substitute one?
      var got = prop.value.font || "";
      if (t.font && got && got.toLowerCase().replace(/[^a-z]/g, "").indexOf(t.font.toLowerCase().replace(/[^a-z]/g, "").slice(0, 6)) < 0)
        warn("font '" + t.font + "' not installed — AE used '" + got + "'. Install the TTFs in the _assets/fonts folder.");
    } catch (e) {}
    if (t.stretch && t.stretch !== 100) {
      layer.property("ADBE Transform Group").property("ADBE Scale").setValue([t.stretch, 100]);
    }
  }

  function shapeGroup(layer, sh) {
    var root = layer.property("ADBE Root Vectors Group");
    var grp = root.addProperty("ADBE Vector Group");
    var contents = grp.property("ADBE Vectors Group");
    var ctx = {};
    if (sh.kind === "grid") {
      var r = contents.addProperty("ADBE Vector Shape - Rect");
      r.property("ADBE Vector Rect Size").setValue([sh.square, sh.square]);
      r.property("ADBE Vector Rect Position").setValue([sh.square / 2, sh.square / 2]);
      var f = contents.addProperty("ADBE Vector Graphic - Fill");
      f.property("ADBE Vector Fill Color").setValue(sh.fill);
      ctx.fill = f;
      var cols = Math.max(1, Math.round(sh.size[0] / sh.cell)), rows = Math.max(1, Math.round(sh.size[1] / sh.cell));
      var rx = contents.addProperty("ADBE Vector Filter - Repeater");          // columns
      rx.property("ADBE Vector Repeater Copies").setValue(cols);
      rx.property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Position").setValue([sh.cell, 0]);
      var ry = contents.addProperty("ADBE Vector Filter - Repeater");          // rows
      ry.property("ADBE Vector Repeater Copies").setValue(rows);
      ry.property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Position").setValue([0, sh.cell]);
    } else {
      var rect = contents.addProperty("ADBE Vector Shape - Rect");
      rect.property("ADBE Vector Rect Size").setValue(sh.size);
      rect.property("ADBE Vector Rect Position").setValue([sh.size[0] / 2, sh.size[1] / 2]);
      if (sh.radius) rect.property("ADBE Vector Rect Roundness").setValue(sh.radius);
      if (sh.fill) {
        var fl = contents.addProperty("ADBE Vector Graphic - Fill");
        fl.property("ADBE Vector Fill Color").setValue(sh.fill);
        ctx.fill = fl;
      }
      if (sh.stroke) {
        var st = contents.addProperty("ADBE Vector Graphic - Stroke");
        st.property("ADBE Vector Stroke Color").setValue(sh.stroke);
        st.property("ADBE Vector Stroke Width").setValue(sh.strokeW || 4);
        ctx.stroke = st;
      }
      if (sh.trim) {
        var tr = contents.addProperty("ADBE Vector Filter - Trim");
        ctx.trim = tr;
      }
    }
    return ctx;
  }

  function build(scene) {
    var proj = app.project || app.newProject();
    app.beginUndoGroup("Motion Lab — " + scene.comp.name);
    var c = scene.comp;
    var comp = proj.items.addComp(c.name, c.w, c.h, 1, c.duration, c.fps);
    comp.bgColor = c.bg;

    // imported assets (icons, screenshots) live next to the script in <name>_assets/
    var assets = {}, scriptFile = new File($.fileName), base = scriptFile.parent;
    for (var a = 0; a < (scene.assets || []).length; a++) {
      var spec = scene.assets[a], f = new File(base.fsName + "/" + spec.file);
      if (f.exists) {
        try { assets[spec.id] = proj.importFile(new ImportOptions(f)); }
        catch (e) { warn("import " + spec.file); }
      } else warn("missing asset " + spec.file);
    }

    var byName = {};
    for (var i = 0; i < scene.layers.length; i++) {
      var L = scene.layers[i], layer = null, ctx = { offset: null };
      try {
        if (L.kind === "solid") {
          layer = comp.layers.addSolid(L.color, L.name, L.size[0], L.size[1], 1);
        } else if (L.kind === "text") {
          layer = comp.layers.addText(L.text.value);
          setText(layer, L.text);
        } else if (L.kind === "shape") {
          layer = comp.layers.addShape(); layer.name = L.name;
          ctx = shapeGroup(layer, L.shape);
        } else if (L.kind === "footage") {
          if (!assets[L.asset]) { warn("no asset " + L.asset); continue; }
          layer = comp.layers.add(assets[L.asset]);
          layer.name = L.name;
          if (L.size && L.size[0]) {
            var src = layer.source;
            layer.property("ADBE Transform Group").property("ADBE Scale")
              .setValue([L.size[0] / src.width * 100, (L.size[1] || L.size[0]) / src.height * 100]);
          }
        } else if (L.kind === "null") {
          layer = comp.layers.addNull(c.duration); layer.name = L.name;
        }
        if (!layer) continue;

        var tr = layer.property("ADBE Transform Group");
        if (L.kind !== "text") {                      // top-left anchoring, like the HTML templates
          try {
            if (L.kind === "solid" || L.kind === "null") tr.property("ADBE Anchor Point").setValue([0, 0]);
            else if (L.kind === "footage") tr.property("ADBE Anchor Point").setValue([0, 0]);
          } catch (e) {}
        }
        tr.property("ADBE Position").setValue(L.pos || [0, 0]);

        addEffects(layer, L.effects);
        if (L.mask) addMask(layer, L.mask);
        for (var p in L.props) if (L.props.hasOwnProperty(p)) applyProp(layer, p, L.props[p], ctx);
        if (L["in"] !== undefined) layer.inPoint = L["in"];
        if (L["out"] !== undefined) layer.outPoint = L["out"];
        byName[L.name] = layer;
      } catch (err) { warn("layer '" + L.name + "': " + err.toString()); }
    }

    for (var j = 0; j < scene.layers.length; j++) {   // parenting after every layer exists
      var pl = scene.layers[j];
      if (pl.parent && byName[pl.name] && byName[pl.parent]) {
        try { byName[pl.name].parent = byName[pl.parent]; } catch (e) { warn("parent " + pl.name); }
      }
    }

    comp.openInViewer();
    app.endUndoGroup();
    try {                                                     // log beside the script: motion-lab-ae.log
      var lf = new File(base.fsName + "/motion-lab-ae.log");
      lf.open("w");
      lf.writeln("Motion Lab AE build — " + new Date().toString());
      lf.writeln("comp: " + c.name + "  " + c.w + "x" + c.h + " @" + c.fps + "fps  " + c.duration + "s");
      lf.writeln("layers built: " + scene.layers.length);
      lf.writeln(WARN.length ? "warnings:" : "warnings: none");
      for (var wi = 0; wi < WARN.length; wi++) lf.writeln("  - " + WARN[wi]);
      lf.close();
    } catch (e) {}
    var msg = "Built '" + c.name + "' — " + scene.layers.length + " layers.";
    if ((scene.notes || []).length) msg += "\n\nNotes:\n• " + scene.notes.join("\n• ");
    if (WARN.length) msg += "\n\nNot fully supported here:\n• " + WARN.join("\n• ");
    msg += "\n\nA log was written next to this script (motion-lab-ae.log) — send it back if anything looks wrong.";
    alert(msg);
  }

  return { build: build };
})();
