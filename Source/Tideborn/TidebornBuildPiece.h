#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TidebornBuildPiece.generated.h"

UCLASS()
class TIDEBORN_API ATidebornBuildPiece : public AActor
{
	GENERATED_BODY()

public:
	ATidebornBuildPiece();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn")
	TObjectPtr<UStaticMeshComponent> Mesh;

	void ConfigureAsGhost();
	void ConfigureAsPlaced();
};
