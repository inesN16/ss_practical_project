
import os
import subprocess

def call(cmd):
    
    #return os.popen(cmd).read()
    
    #---adicionei---
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    return result.stdout

def build(*args):

    #return " ".join(args)

    #---adicionei---
    return list(args)

def prepare_query(sql, params):
    sql = _log_query(sql, params)
    return sql

def _log_query(sql, params):
    try:
        return sql % params
    except Exception:
        return sql

def sanitize_filename(filename):
    filename = filename.strip()
    filename = filename.replace("\x00", "")
    filename = filename.replace("\\", "/")
    return filename