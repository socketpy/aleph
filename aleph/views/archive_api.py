import logging
from flask.wrappers import Response
from flask import Blueprint, redirect, send_file, request

from aleph.core import archive
from aleph.logic.util import archive_claim
from aleph.views.util import require
from aleph.views.context import tag_request

log = logging.getLogger(__name__)
blueprint = Blueprint("archive_api", __name__)


@blueprint.route("/api/2/archive")
def retrieve():
    """Downloads a binary blob from the blob storage archive.
    ---
    get:
      summary: Download a blob from the archive
      parameters:
      - description: Authorization token for an archive blob
        in: query
        name: claim
        schema:
          type: string
          description: A signed JWT with the object hash.
      responses:
        '200':
          description: OK
          content:
            '*/*': {}
        '404':
          description: Object does not exist.
      tags:
      - Archive
    """
    claim = request.args.get("claim")
    role_id, content_hash, file_name, mime_type = archive_claim(claim)
    require(request.authz.id == role_id)
    tag_request(content_hash=content_hash, file_name=file_name)
    url = archive.generate_url(content_hash, file_name=file_name, mime_type=mime_type)
    if url is not None:
        return redirect(url)
    try:
        local_path = archive.load_file(content_hash)
        if local_path is None:
            return Response(status=404)
        return send_file(
            str(local_path),
            as_attachment=True,
            conditional=True,
            attachment_filename=file_name,
            mimetype=mime_type,
        )
    finally:
        archive.cleanup_file(content_hash)
