from flask import render_template, request, redirect, url_for, session

def login_view():
    from app import app
    if request.method=="POST":
        if request.form.get("usuario")=="decano" and request.form.get("clave")=="comap2026":
            session["admin"] = True
            return redirect(url_for("admin_page"))
        return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

def logout_view():
    from flask import session, redirect, url_for
    session.clear()
    return redirect(url_for("login_page"))
