from jinja2 import Environment, FileSystemLoader, select_autoescape

class Html(object):

    def renderHtml(context, html_config):
        # Create a Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(html_config['dir']),
            autoescape=select_autoescape(['j2'])
        )

        # Load the template file
        template = env.get_template(html_config['file'])

        # Render the template with the provided context
        rendered_content = template.render(context)

        # Write the rendered content to the output file
        with open(html_config['dest'], 'w') as file:
            file.write(rendered_content)
            print(f"SUCCESS: {html_config['dest']} updated successfully")
