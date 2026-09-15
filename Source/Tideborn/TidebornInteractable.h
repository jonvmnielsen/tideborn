#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "TidebornInteractable.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UTidebornInteractable : public UInterface
{
	GENERATED_BODY()
};

class TIDEBORN_API ITidebornInteractable
{
	GENERATED_BODY()

public:
	virtual bool Tideborn_TryInteract(AActor* Interactor) = 0;
};
