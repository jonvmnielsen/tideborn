#pragma once
#include "CoreMinimal.h"
#include "TidebornCreature.h"
#include "TidebornKelpBack.generated.h"

class UStaticMeshComponent;

UCLASS()
class TIDEBORN_API ATidebornKelpBack : public ATidebornCreature
{
	GENERATED_BODY()
public:
	ATidebornKelpBack();

	/** Mid + top spheres for a taller rounded stack silhouette. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> MidMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> TopMesh;
};
