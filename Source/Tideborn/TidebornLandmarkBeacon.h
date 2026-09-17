#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TidebornLandmarkBeacon.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;

/** Tall thin path marker with warm light — guidance ladder step 1 (landmark/light). */
UCLASS()
class TIDEBORN_API ATidebornLandmarkBeacon : public AActor
{
	GENERATED_BODY()

public:
	ATidebornLandmarkBeacon();

	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> PostMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UPointLightComponent> WarmLight;
};
