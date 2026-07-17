{{/* Common labels used across resources */}}
{{- define "gitops-demo-app.labels" -}}
app: {{ .Release.Name }}
managed-by: {{ .Release.Service }}
{{- end -}}
