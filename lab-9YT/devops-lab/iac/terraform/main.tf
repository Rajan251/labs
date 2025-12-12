resource "local_file" "foo" {
  content  = "Hello, DevOps World!"
  filename = "${path.module}/hello.txt"
}
