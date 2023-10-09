text="Ahoj Pepo"
echo $text
curl -d '{"message":"Ahoj Pepo"}' -H "Content-Type: application/json" -X POST https://salesgpt.3dmemories.eu/chat
#http://172.29.124.103:91/chat