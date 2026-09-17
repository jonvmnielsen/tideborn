#pragma once
#include "CoreMinimal.h"
#include "TidebornCreature.h"
#include "TidebornBurrHound.generated.h"

class UStaticMeshComponent;

UCLASS()
class TIDEBORN_API ATidebornBurrHound : public ATidebornCreature
{
	GENERATED_BODY()
public:
	ATidebornBurrHound();

	/** Short snout/head cube — silhouette reads hostile without relying on color. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> HeadMesh;
};
