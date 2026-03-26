from flask import abort

# 起動エラー回避用スタブ、barchartブランチマージ時に上書きすること


def handle_gadget_data(gadget_uuid):
    abort(501)


def handle_gadget_csv_export(gadget_uuid):
    abort(501)


def handle_gadget_create(gadget_type):
    abort(501)


def handle_gadget_register(gadget_type):
    abort(501)
