# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "https://s3-us-west-2.amazonaws.com/gina-vagrant-boxes/win7x64-pro.box"
  config.vm.box_check_update = false

  config.vm.synced_folder ".", "/Users/vagrant/Desktop/aaem"

  config.vm.provider "virtualbox" do |vb|
    vb.gui = true
    vb.memory = "1024"
  end
end
