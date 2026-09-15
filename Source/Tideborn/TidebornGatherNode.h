#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TidebornInteractable.h"
#include "TidebornGatherNode.generated.h"

UCLASS()
class TIDEBORN_API ATidebornGatherNode : public AActor, public ITidebornInteractable
{
	GENERATED_BODY()

public:
	ATidebornGatherNode();

	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn")
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Gather")
	FName ItemId = FName(TEXT("Wood"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Gather")
	int32 AmountPerGather = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Gather")
	int32 RemainingUses = 8;

	virtual bool Tideborn_TryInteract(AActor* Interactor) override;
};
