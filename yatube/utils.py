def print_form_errors(form):
    for field in form.errors:
        print(f'Field "{field}" error: {form.errors[field].as_text()}')
