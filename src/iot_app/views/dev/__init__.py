from flask import Blueprint, render_template, g, request

dev_bp = Blueprint('dev', __name__, url_prefix='/dev')


@dev_bp.before_request
def set_mock_user():
    uid = request.args.get('uid', type=int)
    if uid is not None:
        g.current_user.user_type_id = uid


@dev_bp.route('/preview')
def preview():
    return render_template('dev/preview.html')
