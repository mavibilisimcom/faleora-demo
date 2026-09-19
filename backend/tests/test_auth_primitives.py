from auth import ph,pv,th
def test_password_hash_roundtrip():
 h=ph("very-secure-password")
 assert pv("very-secure-password",h)
 assert not pv("wrong-password",h)
def test_token_hash_stable():
 assert th("abc")==th("abc")
 assert th("abc")!=th("abcd")
