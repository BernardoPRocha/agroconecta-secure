terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "ssh_public_key_path" {
  description = "Caminho da chave pública já criada (não envie chave privada ao Terraform)."
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_allowed_cidr" {
  description = "IP público de administração em CIDR, por exemplo 203.0.113.4/32. NÃO use 0.0.0.0/0."
  type        = string
  validation {
    condition     = can(cidrhost(var.ssh_allowed_cidr, 0)) && var.ssh_allowed_cidr != "0.0.0.0/0"
    error_message = "Informe um CIDR válido e restrito; 0.0.0.0/0 não é permitido para SSH."
  }
}

variable "dns_label" {
  description = "Nome DNS globalmente exclusivo em brazilsouth.cloudapp.azure.com."
  type        = string
  default     = "agroconecta-bernardo-gs2026"
}

resource "azurerm_resource_group" "rg_agro" {
  name     = "rg-agroconecta-prod"
  location = "Brazil South"
}

resource "azurerm_virtual_network" "vnet_agro" {
  name                = "vnet-agroconecta"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg_agro.location
  resource_group_name = azurerm_resource_group.rg_agro.name
}

resource "azurerm_subnet" "subnet_agro" {
  name                 = "subnet-mvp"
  resource_group_name  = azurerm_resource_group.rg_agro.name
  virtual_network_name = azurerm_virtual_network.vnet_agro.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "pip_agro" {
  name                = "pip-agroconecta-mvp"
  location            = azurerm_resource_group.rg_agro.location
  resource_group_name = azurerm_resource_group.rg_agro.name
  allocation_method   = "Static"
  sku                 = "Standard"
  domain_name_label   = var.dns_label
}

resource "azurerm_network_security_group" "nsg_agro" {
  name                = "nsg-agroconecta"
  location            = azurerm_resource_group.rg_agro.location
  resource_group_name = azurerm_resource_group.rg_agro.name

  security_rule {
    name                       = "Allow-SSH-Admin-Only"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.ssh_allowed_cidr
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Allow-AgroConecta-HTTP-HTTPS"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["80", "443"]
    source_address_prefix      = var.ssh_allowed_cidr
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "nic_agro" {
  name                = "nic-agroconecta"
  location            = azurerm_resource_group.rg_agro.location
  resource_group_name = azurerm_resource_group.rg_agro.name
  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.subnet_agro.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip_agro.id
  }
}

resource "azurerm_network_interface_security_group_association" "nsg_assoc" {
  network_interface_id      = azurerm_network_interface.nic_agro.id
  network_security_group_id = azurerm_network_security_group.nsg_agro.id
}

resource "azurerm_linux_virtual_machine" "vm_agro" {
  name                            = "vm-agroconecta-mvp"
  resource_group_name             = azurerm_resource_group.rg_agro.name
  location                        = azurerm_resource_group.rg_agro.location
  size                            = var.vm_size
  admin_username                  = "azureuser"
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.nic_agro.id]
  depends_on                      = [azurerm_network_interface_security_group_association.nsg_assoc]

  admin_ssh_key {
    username   = "azureuser"
    public_key = file(pathexpand(var.ssh_public_key_path))
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 64
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  custom_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu jammy stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
    usermod -aG docker azureuser
    EOF
  )

  tags = {
    Project     = "AgroConecta-GS2026"
    Environment = "Academic-MVP"
  }
}

output "url_publica_mvp" {
  value = "https://${azurerm_public_ip.pip_agro.fqdn}"
}

output "ip_publico_vm" {
  value = azurerm_public_ip.pip_agro.ip_address
}

variable "subscription_id" { type = string }
variable "github_repository" {
  description = "Repositório Secure no formato usuario/repositorio; não use URL."
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "Informe usuario/repositorio."
  }
}
variable "vm_size" {
  description = "8 GB para ACV CPU + Grafana + Prometheus; confirme preço/cota antes de aplicar."
  type        = string
  default     = "Standard_B2ms"
}
resource "azurerm_user_assigned_identity" "github" {
  name                = "agroconecta-github-deploy"
  location            = azurerm_resource_group.rg_agro.location
  resource_group_name = azurerm_resource_group.rg_agro.name
}
resource "azurerm_federated_identity_credential" "github" {
  name                = "github-production"
  resource_group_name = azurerm_resource_group.rg_agro.name
  parent_id           = azurerm_user_assigned_identity.github.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  subject             = "repo:BernardoPRocha@126582923/agroconecta-secure@1460562175:environment:production"
}
resource "azurerm_role_assignment" "deploy_vm" {
  scope                = azurerm_linux_virtual_machine.vm_agro.id
  role_definition_name = "Virtual Machine Contributor"
  principal_id         = azurerm_user_assigned_identity.github.principal_id
}
data "azurerm_client_config" "current" {}
output "github_azure_client_id" { value = azurerm_user_assigned_identity.github.client_id }
output "github_azure_tenant_id" { value = data.azurerm_client_config.current.tenant_id }
output "github_azure_subscription_id" { value = var.subscription_id }
output "github_azure_resource_group" { value = azurerm_resource_group.rg_agro.name }
output "github_azure_vm_name" { value = azurerm_linux_virtual_machine.vm_agro.name }
output "github_site_domain" { value = azurerm_public_ip.pip_agro.fqdn }
