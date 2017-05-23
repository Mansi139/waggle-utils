from flask import Flask, request
from flask import jsonify
from flask import render_template
import stats
import click
import subprocess
import sqlite3 as sql
import json
import time

app = Flask(__name__)


@app.route('/loadavg')
def loadavg():
    return jsonify(stats.loadavg())


@app.route('/cpu')
def cpustats():
    return jsonify(stats.cpustats())


@app.route('/mem')
def memstats():
    return jsonify(stats.meminfo())


@app.route('/mounts')
def mounts():
    return jsonify(stats.mounts())


@app.route('/ip/route')
def ip_route():
    return jsonify(stats.ip_route())


@app.route('/enternew')
def new_student():
    return render_template('student.html')

@app.route('/uptime')
def uptime():
    return jsonify(stats.uptime())


@app.route('/blocks')
def blocks():
    return jsonify(stats.listblocks())


@app.route('/blocks/<block>')
def blockinfo(block):
    try:
        return jsonify(stats.blockinfo(block))
    except FileNotFoundError:
        return 'Block not found.', 404


@app.route('/devices')
def devices():
    return jsonify(stats.devices())


@app.route('/version')
def version():
    return jsonify(stats.version())

@app.route('/')
def index():
    with sql.connect("test.db") as con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS observations(
            date_time TEXT,
            type TEXT not null,
            data BLOB);''')
        
        con.commit()
    return render_template('index.html')
