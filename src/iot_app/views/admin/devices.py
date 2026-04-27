from datetime import datetime

from flask import abort, flash, g, jsonify, make_response, redirect, render_template, request, url_for

from iot_app.common.cookie import (
    get_search_conditions_cookie,
    set_search_conditions_cookie,
)
from iot_app.decorators.auth import require_role
from iot_app.forms.device import DeviceCreateForm, DeviceUpdateForm
from iot_app.services.device_service import (
    DuplicateDeviceIdError,
    DuplicateMacAddressError,
    create_device,
    delete_device,
    generate_devices_csv,
    get_all_devices_for_export,
    get_default_search_params,
    get_device_by_uuid,
    get_device_form_options,
    get_device_status_map,
    search_devices,
    update_device,
)
from iot_app.views.admin import admin_bp


@admin_bp.route('/devices', methods=['GET'])
@require_role('system_admin', 'management_admin', 'sales_company_user', 'service_company_user')
def devices_list():
    if 'page' not in request.args:
        search_params = get_default_search_params()
    else:
        search_params = get_search_conditions_cookie('devices') or get_default_search_params()
        search_params['page'] = request.args.get('page', 1, type=int)

    try:
        devices, total = search_devices(search_params, g.current_user.user_id)
        device_types, organizations, sort_items = get_device_form_options(g.current_user.user_id)
        status_map = get_device_status_map([d.device_id for d in devices])
    except Exception:
        abort(500)

    response = make_response(render_template(
        'admin/devices/list.html',
        devices=devices,
        total=total,
        search_params=search_params,
        device_types=device_types,
        organizations=organizations,
        sort_items=sort_items,
        status_map=status_map,
    ))
    response = set_search_conditions_cookie(response, 'devices', search_params)
    return response


@admin_bp.route('/devices', methods=['POST'])
@require_role('system_admin', 'management_admin', 'sales_company_user', 'service_company_user')
def search_devices_view():
    raw_device_type_id = request.form.get('device_type_id')
    raw_organization_id = request.form.get('organization_id')

    search_params = {
        'page': 1,
        'per_page': get_default_search_params()['per_page'],
        'sort_by': request.form.get('sort_by', ''),
        'order': request.form.get('order', ''),
        'device_id': request.form.get('device_id', ''),
        'device_name': request.form.get('device_name', ''),
        'device_type_id': int(raw_device_type_id) if raw_device_type_id else None,
        'location': request.form.get('location', ''),
        'organization_id': int(raw_organization_id) if raw_organization_id else None,
        'certificate_expiration_date': request.form.get('certificate_expiration_date', ''),
        'status': request.form.get('status') or None,
    }

    response = make_response(redirect(url_for('admin.devices_list', page=1)))
    response = set_search_conditions_cookie(response, 'devices', search_params)
    return response


@admin_bp.route('/devices/create', methods=['GET'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def create_device_form():
    try:
        device_types, organizations, _ = get_device_form_options(g.current_user.user_id)
    except Exception:
        abort(500)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            'admin/devices/create_modal.html',
            device_types=device_types,
            organizations=organizations,
        )
    return render_template(
        'admin/devices/form.html',
        mode='create',
        device_types=device_types,
        organizations=organizations,
    )


@admin_bp.route('/devices/register', methods=['POST'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def create_device_view():
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    form = DeviceCreateForm(request.form)

    try:
        device_types, organizations, _ = get_device_form_options(g.current_user.user_id)
    except Exception:
        abort(500)
    form.device_type_id.choices = [(dt.device_type_id, dt.device_type_name) for dt in device_types]
    form.organization_id.choices = [(org.organization_id, org.organization_name) for org in organizations]

    if not form.validate_on_submit():
        tmpl = 'admin/devices/create_modal.html' if is_ajax else 'admin/devices/form.html'
        kwargs = dict(form=form, device_types=device_types, organizations=organizations)
        if not is_ajax:
            kwargs['mode'] = 'create'
        return render_template(tmpl, **kwargs), 400

    device_data = {
        'device_uuid': form.device_uuid.data,
        'device_name': form.device_name.data,
        'device_type_id': form.device_type_id.data,
        'device_model': form.device_model.data or None,
        'sim_id': form.sim_id.data or None,
        'mac_address': form.mac_address.data or None,
        'device_location': form.device_location.data or None,
        'organization_id': form.organization_id.data,
        'certificate_expiration_date': form.certificate_expiration_date.data,
    }

    try:
        create_device(device_data, g.current_user.user_id)
    except DuplicateDeviceIdError:
        form.device_uuid.errors.append('このデバイスIDは既に登録されています')
        tmpl = 'admin/devices/create_modal.html' if is_ajax else 'admin/devices/form.html'
        kwargs = dict(form=form, device_types=device_types, organizations=organizations)
        if not is_ajax:
            kwargs['mode'] = 'create'
        return render_template(tmpl, **kwargs), 400
    except DuplicateMacAddressError:
        form.mac_address.errors.append('このMACアドレスは既に登録されています')
        tmpl = 'admin/devices/create_modal.html' if is_ajax else 'admin/devices/form.html'
        kwargs = dict(form=form, device_types=device_types, organizations=organizations)
        if not is_ajax:
            kwargs['mode'] = 'create'
        return render_template(tmpl, **kwargs), 400
    except Exception:
        abort(500)

    if is_ajax:
        return jsonify({'message': 'デバイスを登録しました'})
    flash('デバイスを登録しました', 'success')
    return redirect(url_for('admin.devices_list'))


@admin_bp.route('/devices/delete', methods=['POST'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def delete_device_view():
    device_uuids = request.form.getlist('device_uuids')
    if not device_uuids:
        flash('削除するデバイスを選択してください', 'error')
        return redirect(url_for('admin.devices_list'))

    deleted_count = 0
    for device_uuid in device_uuids:
        try:
            device = get_device_by_uuid(device_uuid, g.current_user.user_id)
        except Exception:
            abort(500)

        if not device:
            flash('指定されたデバイスが見つかりません', 'error')
            continue

        try:
            delete_device(device, g.current_user.user_id)
        except Exception:
            abort(500)

        deleted_count += 1

    if deleted_count > 0:
        flash(f'{deleted_count}件のデバイスを削除しました', 'success')
    return redirect(url_for('admin.devices_list'))


@admin_bp.route('/devices/export', methods=['POST'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def export_devices_csv_view():
    search_params = get_search_conditions_cookie('devices') or get_default_search_params()

    try:
        devices = get_all_devices_for_export(search_params, g.current_user.user_id)
        csv_data = generate_devices_csv(devices)
    except Exception:
        abort(500)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f'attachment; filename="devices_{timestamp}.csv"'
    return response


@admin_bp.route('/devices/<device_uuid>', methods=['GET'])
@require_role('system_admin', 'management_admin', 'sales_company_user', 'service_company_user')
def view_device_detail(device_uuid):
    try:
        device = get_device_by_uuid(device_uuid, g.current_user.user_id)
    except Exception:
        abort(500)
    if not device:
        abort(404)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            device_types, organizations, _ = get_device_form_options(g.current_user.user_id)
            status_map = get_device_status_map([device.device_id])
        except Exception:
            abort(500)
        return render_template(
            'admin/devices/detail_modal.html',
            device=device,
            device_types=device_types,
            organizations=organizations,
            status_map=status_map,
        )
    return render_template('admin/devices/detail.html', device=device)


@admin_bp.route('/devices/<device_uuid>/edit', methods=['GET'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def edit_device_form(device_uuid):
    try:
        device = get_device_by_uuid(device_uuid, g.current_user.user_id)
    except Exception:
        abort(500)
    if not device:
        abort(404)

    try:
        device_types, organizations, _ = get_device_form_options(g.current_user.user_id)
    except Exception:
        abort(500)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            'admin/devices/edit_modal.html',
            device=device,
            device_types=device_types,
            organizations=organizations,
        )
    return render_template(
        'admin/devices/form.html',
        mode='edit',
        device=device,
        device_types=device_types,
        organizations=organizations,
    )


@admin_bp.route('/devices/<device_uuid>/update', methods=['POST'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def update_device_view(device_uuid):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    form = DeviceUpdateForm(request.form)

    try:
        device = get_device_by_uuid(device_uuid, g.current_user.user_id)
        device_types, organizations, _ = get_device_form_options(g.current_user.user_id)
    except Exception:
        abort(500)
    if not device:
        abort(404)
    form.device_type_id.choices = [(dt.device_type_id, dt.device_type_name) for dt in device_types]
    form.organization_id.choices = [(org.organization_id, org.organization_name) for org in organizations]

    if not form.validate_on_submit():
        tmpl = 'admin/devices/edit_modal.html' if is_ajax else 'admin/devices/form.html'
        kwargs = dict(form=form, device=device, device_types=device_types, organizations=organizations)
        if not is_ajax:
            kwargs['mode'] = 'edit'
        return render_template(tmpl, **kwargs), 400

    device_data = {
        'device_name': form.device_name.data,
        'device_type_id': form.device_type_id.data,
        'device_model': form.device_model.data or None,
        'sim_id': form.sim_id.data or None,
        'mac_address': form.mac_address.data or None,
        'device_location': form.device_location.data or None,
        'organization_id': form.organization_id.data,
        'certificate_expiration_date': form.certificate_expiration_date.data,
    }

    try:
        update_device(device_uuid, device_data, g.current_user.user_id)
    except DuplicateMacAddressError:
        form.mac_address.errors.append('このMACアドレスは既に登録されています')
        tmpl = 'admin/devices/edit_modal.html' if is_ajax else 'admin/devices/form.html'
        kwargs = dict(form=form, device=device, device_types=device_types, organizations=organizations)
        if not is_ajax:
            kwargs['mode'] = 'edit'
        return render_template(tmpl, **kwargs), 400
    except Exception:
        abort(500)

    if is_ajax:
        return jsonify({'message': 'デバイスを更新しました'})
    flash('デバイスを更新しました', 'success')
    return redirect(url_for('admin.devices_list'))
