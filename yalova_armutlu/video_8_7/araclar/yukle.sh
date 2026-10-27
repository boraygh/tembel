#!/bin/bash
# Higgsfield imzalı yükleme: yukle.sh DOSYA CONTENT_TYPE 'UPLOAD_URL'
curl -sS -X PUT -H "Content-Type: $2" -H "If-None-Match: *" --data-binary @"$1" "$3" -w "%{http_code}\n"
