* IGBT PhysNet OSDI sweep test

.model igbt_physnet igbt_physnet    

Vg g 0 DC 17
Va a 0 DC 2
ni1 a g c igbt_physnet
R1 c 0 0.0001


*.temp 150

*.print DC V(a) V(g) V(c) I(Va)
.control
pre_osdi /root/autodl-tmp/my_hefner/VA-Models/code/IGBT_PhysNet/igbt_physnet.osdi

dc Va 0.2 10 0.05
*wrdata /root/autodl-tmp/my_hefner/nntest/physnet_data/physnet_vge17_t150.raw abs(v(c))
wrdata /root/autodl-tmp/my_hefner/nntest/physnet_data/physnet_vge17_t150.raw  abs(I(Va))
quit
.endc
.end
