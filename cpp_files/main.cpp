#include "Component.h"
#include "MasterComponent.h"

int main()
{
    Base::Component::Example example;
    Base::Component::MasterExample masterExample;
    
    example.run();
    masterExample.run();
    
    Base::Sub::Component::Sub2::MasterCWrapper master;
    Base::Unit::Example useMasterInPlaceOfSingle(master, master, master);
}