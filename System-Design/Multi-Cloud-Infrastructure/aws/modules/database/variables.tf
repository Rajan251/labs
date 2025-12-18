variable "cluster_identifier" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "availability_zones" {
  type = list(string)
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "master_username" {
  type    = string
  default = "postgres"
}

variable "master_password" {
  type      = string
  sensitive = true
}

variable "instance_count" {
  type    = number
  default = 2
}

variable "instance_class" {
  type    = string
  default = "db.r6g.large"
}
