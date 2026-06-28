from app.diff_parser import parse_diff

# Sample diff from a simple Python file change
sample_diff = """diff --git a/hello.py b/hello.py
index 1234567..abcdefg 100644
--- a/hello.py
+++ b/hello.py
@@ -1,2 +1,5 @@
 def greet(name):
-    print("Hello, " + name)
+    if name:
+        print("Hello, " + name)
+    else:
+        print("Hello, World!")"""

if __name__ == "__main__":
    parsed = parse_diff(sample_diff)
    print("Parsed diff structure:")
    import json
    print(json.dumps(parsed, indent=2))
